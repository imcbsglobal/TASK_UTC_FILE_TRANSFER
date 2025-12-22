from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from .models import TransferData
import requests
from django.utils.timezone import localtime

CORPORATE_API_URL = "https://activate.imcbs.com/corporate-clientid/list/"


def is_valid_corporate_client(corporate_id, client_id):
    try:
        response = requests.get(CORPORATE_API_URL, timeout=10)
        data = response.json()

        if not data.get("success"):
            return False

        for corp in data.get("data", []):
            if corp.get("corporate_id") == corporate_id:
                for shop in corp.get("shops", []):
                    if shop.get("client_id") == client_id:
                        return True
        return False
    except Exception:
        return False

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.utils.timezone import localtime
from .models import TransferData
import requests

CORPORATE_API_URL = "https://activate.imcbs.com/corporate-clientid/list/"


@csrf_exempt
def transfer_api(request):

    # ===================== GET API =====================
    if request.method == 'GET':

        client_id = request.GET.get("client_id")

        if client_id:
            records = TransferData.objects.filter(
                to_client_id=client_id
            ).order_by('-created_at')
        else:
            records = TransferData.objects.all().order_by('-created_at')

        response_data = []

        for item in records:
            # ✅ Convert UTC → Asia/Kolkata
            local_dt = localtime(item.created_at)

            response_data.append({
                "id": item.id,
                "from_corporate_id": item.from_corporate_id,
                "from_client_id": item.from_client_id,
                "to_corporate_id": item.to_corporate_id,
                "to_client_id": item.to_client_id,
                "type": item.transfer_type,

                # USERS
                "uploaded_user": item.user,
                "completed_user": item.completed_user,

                # STATUS
                "status": item.status,

                # FILES
                "data_1": item.data_1,
                "data_2": item.data_2,

                # ✅ IST DATE & TIME
                "date_of_upload": local_dt.strftime("%Y-%m-%d"),
                "time_of_upload": local_dt.strftime("%I:%M %p"),
            })

        return JsonResponse({
            "success": True,
            "count": len(response_data),
            "data": response_data
        })


    # ===================== POST API =====================
    elif request.method == 'POST':
        try:
            from_corporate_id = request.POST.get('from_corporate_id')
            from_client_id = request.POST.get('from_client_id')
            to_corporate_id = request.POST.get('to_corporate_id')
            to_client_id = request.POST.get('to_client_id')
            transfer_type = request.POST.get('type')
            user = request.POST.get('user')

            file1 = request.FILES.get('data_1')
            file2 = request.FILES.get('data_2')

            # REQUIRED FIELDS
            if not all([
                from_corporate_id,
                from_client_id,
                to_corporate_id,
                to_client_id,
                transfer_type,
                user
            ]):
                return JsonResponse({
                    "success": False,
                    "message": "Missing required fields"
                }, status=400)

            # SAME CORPORATE ONLY
            if from_corporate_id != to_corporate_id:
                return JsonResponse({
                    "success": False,
                    "message": "From and To corporate_id must be the same"
                }, status=400)

            # SAME CLIENT NOT ALLOWED
            if from_client_id == to_client_id:
                return JsonResponse({
                    "success": False,
                    "message": "From and To client_id cannot be the same"
                }, status=400)

            # SAVE FILES
            file1_url = None
            file2_url = None

            if file1:
                path1 = default_storage.save(f"uploads/{file1.name}", file1)
                file1_url = default_storage.url(path1)

            if file2:
                path2 = default_storage.save(f"uploads/{file2.name}", file2)
                file2_url = default_storage.url(path2)

            # SAVE DATA
            transfer = TransferData.objects.create(
                from_corporate_id=from_corporate_id,
                from_client_id=from_client_id,
                to_corporate_id=to_corporate_id,
                to_client_id=to_client_id,
                transfer_type=transfer_type,
                user=user,
                data_1=file1_url,
                data_2=file2_url
            )

            return JsonResponse({
                "success": True,
                "message": "Data uploaded successfully",
                "id": transfer.id
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": str(e)
            }, status=500)

    return JsonResponse({
        "success": False,
        "message": "Method not allowed"
    }, status=405)



def transfer_page(request):
    return render(request, "transfer_view.html")







import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import TransferData

ALLOWED_STATUSES = ["Uploaded", "Complete"]


@csrf_exempt
def transfer_status_update_api(request):

    if request.method != "POST":
        return JsonResponse(
            {"success": False, "message": "Method not allowed"},
            status=405
        )

    try:
        body = json.loads(request.body.decode("utf-8"))

        transfer_id = body.get("id")
        status = body.get("status")
        completed_user = body.get("user")

        if not transfer_id or not status or not completed_user:
            return JsonResponse({
                "success": False,
                "message": "id, status and user are required"
            }, status=400)

        # ✅ STATUS VALIDATION
        if status not in ALLOWED_STATUSES:
            return JsonResponse({
                "success": False,
                "message": "Invalid status. Allowed values: Uploaded, Complete"
            }, status=400)

        transfer = TransferData.objects.get(id=transfer_id)

        transfer.status = status

        # ✅ Only set completed_user when status is Complete
        if status == "Complete":
            transfer.completed_user = completed_user
        else:
            transfer.completed_user = None

        transfer.save()

        return JsonResponse({
            "success": True,
            "message": f"Status updated to {status}"
        })

    except TransferData.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Transfer not found"
        }, status=404)

    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "message": "Invalid JSON body"
        }, status=400)

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)
