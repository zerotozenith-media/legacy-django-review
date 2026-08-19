from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from marriage.forms import MarriageRecordForm, EditMarriageRecordForm

from django.http import JsonResponse
from cities_light.models import Region, Country

from marriage.models import MarriageRecord
from organization.utils import get_user_local_church


@csrf_exempt
def get_regions(request):
    country_id = request.GET.get('country_id')
    country = Country.objects.get(id=country_id)
    regions = Region.objects.filter(country=country).values('id', 'name')
    return JsonResponse(list(regions), safe=False)


class ListMarriageRecordView(LoginRequiredMixin, View):
    """View to handle listing record"""
    template_name = "marriage/list.html"
    login_url = '/authentication/login'
    redirect_field_name = 'next'

    def get(self, request):
        """Render the list."""
        user = request.user
        local_churches = get_user_local_church(user)
        records = MarriageRecord.objects.all()

        if user.role == 4 or user.role == 2:
            records = records.filter(registered_by__local_church__in=local_churches)

        context = {"marriage_records": records}
        return render(request, self.template_name, context)


class CreateMarriageRecordView(LoginRequiredMixin, View):
    """View to handle creating marriage record"""
    template_name = "marriage/add.html"
    login_url = '/authentication/login'
    redirect_field_name = 'next'

    def get(self, request):
        """Render the form."""
        # if request.user.role != 5 and not request.user.is_staff:
        #     messages.error(request, "You are not authorized to create marriage records.")
        #     return redirect('list_marriage_records')

        form = MarriageRecordForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        """Handle form submission."""

        form = MarriageRecordForm(request.POST)
        if form.is_valid():
            try:
                record = form.save()
                messages.success(request, f"Marriage record for {record} successfully added!")
                return redirect('list_marriage_records')
            except Exception as e:
                print(str(e))
                messages.error(request, "Something went wrong.")
                return redirect('add_marriage_record')

        messages.error(request, "Please correct the errors below.")
        return render(request, self.template_name, {'form': form})


class EditMarriageRecordView(LoginRequiredMixin, View):
    """View to handle marriage record editing"""
    template_name = "marriage/edit.html"
    login_url = '/authentication/login'
    redirect_field_name = 'next'

    def get(self, request, pk):
        """Render the form."""
        form = EditMarriageRecordForm(instance_id=pk)
        return render(request, self.template_name, {'form': form, "pk": pk})

    def post(self, request, pk):
        """Handle form submission."""

        form = EditMarriageRecordForm(request.POST, instance_id=pk)
        if form.is_valid():
            try:
                record = form.save()
                messages.success(request, f"Marriage record for {record} successfully updated!")
                return redirect('list_marriage_records')
            except Exception as e:
                print(str(e))
                messages.error(request, "Something went wrong.")
                return redirect('edit_marriage_record', pk=pk)

        messages.error(request, "Please correct the errors below.")
        return render(request, self.template_name, {'form': form, "pk": pk})


@login_required(login_url='/authentication/login')
def delete_marriage_record(request, pk):
    """Handle marriage record deletion."""
    record = get_object_or_404(MarriageRecord, pk=pk)
    record.delete()
    messages.success(request, f"Marriage record for {record} deleted successfully")
    return redirect('list_marriage_records')
