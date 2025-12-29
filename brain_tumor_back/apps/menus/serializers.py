from rest_framework import serializers
from .models import Menu, MenuLabel, MenuRole

class MenuLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuLabel
        fields = ["role", "text"]

class MenuRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuRole
        fields = ["role"]

class MenuSerializer(serializers.ModelSerializer):
    labels = MenuLabelSerializer(many=True)
    roles = MenuRoleSerializer(many=True)
    children = serializers.SerializerMethodField()

    class Meta:
        model = Menu
        fields = [
            "id",
            "path",
            "icon",
            "group_label",
            "breadcrumb_only",
            "labels",
            "roles",
            "children",
        ]

    def get_children(self, obj):
        children = obj.children.all()
        return MenuSerializer(children, many=True).data