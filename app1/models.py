from django.db import models


from django.db import models


class TransferData(models.Model):
    from_corporate_id = models.CharField(max_length=100)
    from_client_id = models.CharField(max_length=100)
    to_corporate_id = models.CharField(max_length=100)
    to_client_id = models.CharField(max_length=100)
    transfer_type = models.CharField(max_length=50)

    user = models.CharField(max_length=100)              # uploaded by
    completed_user = models.CharField(
        max_length=100, null=True, blank=True            # completed by
    )

    status = models.CharField(
        max_length=20, default="Uploaded"                # Uploaded / Complete
    )

    data_1 = models.CharField(max_length=255, null=True, blank=True)
    data_2 = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.from_client_id} → {self.to_client_id} ({self.status})"






