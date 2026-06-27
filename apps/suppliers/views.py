from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsProcurementManagerOrAdmin
from .serializers import SupplierSerializer
from .services import (
    create_supplier, update_supplier, get_supplier, 
    list_suppliers, delete_supplier
)

class SupplierListCreateView(generics.GenericAPIView):
    serializer_class = SupplierSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsProcurementManagerOrAdmin()]
        return [IsAuthenticated()]

    def get(self, request, *args, **kwargs):
        # Extract filter params manually to feed to the service layer
        filters = {
            'city': request.query_params.get('city', None),
            'state': request.query_params.get('state', None)
        }
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        queryset = list_suppliers(filters, page, page_size)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        supplier = create_supplier(serializer.validated_data)
        response_serializer = self.get_serializer(supplier)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class SupplierDetailView(generics.GenericAPIView):
    serializer_class = SupplierSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsProcurementManagerOrAdmin()]
        return [IsAuthenticated()]

    def get(self, request, pk, *args, **kwargs):
        supplier = get_supplier_by_id(pk)
        serializer = self.get_serializer(supplier)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        supplier = update_supplier(pk, serializer.validated_data)
        response_serializer = self.get_serializer(supplier)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        supplier = update_supplier(pk, serializer.validated_data)
        response_serializer = self.get_serializer(supplier)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk, *args, **kwargs):
        delete_supplier(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)