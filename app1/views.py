from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from .models import TransferData
import requests
from django.db.models import Q

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
            # ✅ ONLY TO CLIENT DATA
            records = TransferData.objects.filter(
                to_client_id=client_id
            ).order_by('-created_at')
        else:
            records = TransferData.objects.all().order_by('-created_at')

        response_data = []

        for item in records:
            response_data.append({
                "from_corporate_id": item.from_corporate_id,
                "from_client_id": item.from_client_id,
                "to_corporate_id": item.to_corporate_id,
                "to_client_id": item.to_client_id,
                "type": item.transfer_type,
                "data_1": item.data_1,
                "data_2": item.data_2,
                "date_of_upload": item.created_at.strftime("%Y-%m-%d"),
                "time_of_upload": item.created_at.strftime("%H:%M:%S"),
                "status": "uploaded"
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

            file1 = request.FILES.get('data_1')
            file2 = request.FILES.get('data_2')

            # ---- REQUIRED FIELDS ----
            if not all([
                from_corporate_id,
                from_client_id,
                to_corporate_id,
                to_client_id,
                transfer_type
            ]):
                return JsonResponse({
                    "success": False,
                    "message": "Missing required fields"
                }, status=400)

            # ---- SAME CORPORATE ONLY ----
            if from_corporate_id != to_corporate_id:
                return JsonResponse({
                    "success": False,
                    "message": "From and To corporate_id must be the same"
                }, status=400)

            # ---- SAME CLIENT NOT ALLOWED ----
            if from_client_id == to_client_id:
                return JsonResponse({
                    "success": False,
                    "message": "From and To client_id cannot be the same"
                }, status=400)

            # ---- VALIDATE CORPORATE & CLIENT ----
            if not is_valid_corporate_client(from_corporate_id, from_client_id):
                return JsonResponse({
                    "success": False,
                    "message": "from_client_id does not belong to this corporate"
                }, status=400)

            if not is_valid_corporate_client(to_corporate_id, to_client_id):
                return JsonResponse({
                    "success": False,
                    "message": "to_client_id does not belong to this corporate"
                }, status=400)

            # =================================================
            # ✅ SAVE FILES TO CLOUDFLARE R2
            # =================================================
            file1_url = None
            file2_url = None

            if file1:
                path1 = default_storage.save(f"uploads/{file1.name}", file1)
                file1_url = default_storage.url(path1)

            if file2:
                path2 = default_storage.save(f"uploads/{file2.name}", file2)
                file2_url = default_storage.url(path2)

            # =================================================
            # ✅ SAVE NEW ROW (NO DELETE)
            # =================================================
            transfer = TransferData.objects.create(
                from_corporate_id=from_corporate_id,
                from_client_id=from_client_id,
                to_corporate_id=to_corporate_id,
                to_client_id=to_client_id,
                transfer_type=transfer_type,
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
