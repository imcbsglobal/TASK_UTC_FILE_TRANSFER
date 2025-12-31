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


@csrf_exempt
def transfer_api(request):

    # ===================== GET API =====================
    if request.method == 'GET':

        client_id = request.GET.get("client_id")

        if client_id:
            # ✅ Filter by client_id AND status="Uploaded" ONLY
            records = TransferData.objects.filter(
                to_client_id=client_id,
                status="Uploaded"
            ).order_by('-created_at')
        else:
            # ✅ If no client_id provided, show only Uploaded status
            records = TransferData.objects.filter(
                status="Uploaded"
            ).order_by('-created_at')

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
            import json
            body = json.loads(request.body.decode("utf-8"))

            from_corporate_id = body.get('from_corporate_id')
            from_client_id = body.get('from_client_id')
            to_corporate_id = body.get('to_corporate_id')
            to_client_id = body.get('to_client_id')
            transfer_type = body.get('type')
            user = body.get('user')

            # ✅ NOW NORMAL DATA (STRING)
            data_1 = body.get('data_1')
            data_2 = body.get('data_2')

            # REQUIRED FIELDS (UNCHANGED)
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

            # SAVE DATA (NO FILE HANDLING)
            transfer = TransferData.objects.create(
                from_corporate_id=from_corporate_id,
                from_client_id=from_client_id,
                to_corporate_id=to_corporate_id,
                to_client_id=to_client_id,
                transfer_type=transfer_type,
                user=user,
                data_1=data_1,
                data_2=data_2
            )

            return JsonResponse({
                "success": True,
                "message": "Data uploaded successfully",
                "id": transfer.id
            })

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
    return JsonResponse({
        "success": False,
        "message": "Method not allowed"
    }, status=405)


        


def transfer_page(request):
    return render(request, "transfer_view.html")


# ✅ NEW API FOR THE PAGE - SHOWS ALL STATUSES
@csrf_exempt
def transfer_page_api(request):
    """
    This API is used by transfer_view.html to show ALL statuses
    """
    if request.method == 'GET':
        client_id = request.GET.get("client_id")

        if client_id:
            # Show ALL statuses for this client
            records = TransferData.objects.filter(
                to_client_id=client_id
            ).order_by('-created_at')
        else:
            # Show ALL records with ALL statuses
            records = TransferData.objects.all().order_by('-created_at')

        response_data = []

        for item in records:
            local_dt = localtime(item.created_at)

            response_data.append({
                "id": item.id,
                "from_corporate_id": item.from_corporate_id,
                "from_client_id": item.from_client_id,
                "to_corporate_id": item.to_corporate_id,
                "to_client_id": item.to_client_id,
                "type": item.transfer_type,
                "uploaded_user": item.user,
                "completed_user": item.completed_user,
                "status": item.status,
                "data_1": item.data_1,
                "data_2": item.data_2,
                "date_of_upload": local_dt.strftime("%Y-%m-%d"),
                "time_of_upload": local_dt.strftime("%I:%M %p"),
            })

        return JsonResponse({
            "success": True,
            "count": len(response_data),
            "data": response_data
        })

    return JsonResponse({
        "success": False,
        "message": "Method not allowed"
    }, status=405)


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