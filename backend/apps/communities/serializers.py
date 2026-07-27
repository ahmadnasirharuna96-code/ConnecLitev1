from rest_framework import serializers

from .models import Community, CommunityMembership


class CommunitySerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True)
    is_member = serializers.SerializerMethodField()

    class Meta:
        model = Community
        fields = ["id", "name", "description", "category", "is_verified", "member_count", "is_member", "created_at"]
        read_only_fields = ["id", "is_verified", "member_count", "is_member", "created_at"]

    def get_is_member(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.memberships.filter(user=request.user).exists()


class CommunityMemberSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    user_id = serializers.UUIDField(source="user.id", read_only=True)

    class Meta:
        model = CommunityMembership
        fields = ["user_id", "full_name", "role", "joined_at"]
        read_only_fields = fields
