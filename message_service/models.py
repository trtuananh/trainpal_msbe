from djongo import models

class ChatRoom(models.Model):
    user_ids = models.ArrayField(models.IntegerField())
    booking_session_id = models.IntegerField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ChatRoom {self.id} with users {self.user_ids}"

class Message(models.Model):
    sender_id = models.IntegerField()
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender_id} in room {self.room_id}"

class LastSeen(models.Model):
    user_id = models.IntegerField()
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="last_seens")
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Last seen for user {self.user_id} in room {self.room_id}"

    class Meta:
        unique_together = ('user_id', 'room')
        