import re

from django.http import HttpResponseForbidden
from django.urls import resolve
from django.shortcuts import render, redirect
from enum import Enum
import traceback
import logging

logger = logging.getLogger(__name__)


class Role(Enum):
    member = 1
    local_church_pastor = 2
    national_overseer = 3
    region_overseer = 4
    marriage_records = 5


class Authorization:
    def __init__(self, get_response):
        self.get_response = get_response

    def role_based_permissions(self, role):
        permissions = dict()

        permissions["public"] = [
            "dashboard",
            "register",
            "login",
            "validate-username",
            "validate_email",
            "logout",
            "request-password",
            "activate",
            "reset-user-password"
        ]
        permissions["member"] = permissions["public"]+[
            "user_profile",
        ]
        permissions["marriage_records"] = permissions["member"] + [
            "list_marriage_records",
            "add_marriage_record",
            "get_regions",
            "edit_marriage_record",
            "delete_marriage_record",
            'help',
        ]
        permissions['local_church_pastor'] = permissions["member"]+[
            "expenses",
            "add-expenses",
            "expense-delete",
            "expense-edit",
            "search-expenses",
            "get-subcategories",
            "income",
            "add-income",
            "income-edit",
            "income-delete",
            "search_income",
            "source-income",
            "source-list",
            "source-income-update-delete",
            "attendance_list",
            "add_attendance",
            "edit_attendance",
            "delete_attendance",
            "cash-donation",
            "cash-donation-list",
            "interac_uploader",
            "download_interac_sample",
            "offering_uploader",
            "church_service_view",
            # Contribution recording and viewing. Pastors may record and view
            # contributions but must NOT generate tax receipts: those are in
            # receipt_permissions below, given only to the two overseer roles.
            "cash-donation-edit",
            "offerings_USD_edit",
            "offerings_usd_add",
            "offerings_usd_list",
            "offerings",
            "interac_transfer_list",
            "bank_statement_importer",
            "add-interac",
            "add-single-interac",
            "direct_transfer",
            "cheque_deposit",
            "interec_e_transfer",
        ]
        # Tax receipt endpoints. Per system documentation, only National
        # Overseers and Region Overseers may generate and manage tax receipts.
        # Previously these sat only in the national_overseer list, while
        # region_overseer was assigned exactly the pastor set. That was
        # invisible while the "contributor" prefix went unchecked, but would
        # lock region overseers out of receipts the moment checking was
        # enabled. Extracted here so both overseer roles receive them.
        receipt_permissions = [
            "receipts_generation_page",
            "offering_can_summary_report",
            "send_offerings_can_summary_report",
            "send_interac_summary_report",
            "offerings_can_letter_report",
            "interac_summary_report",
            "interac_letter_report",
            "offering_uploader",
            "preview_offerings_can_summary_report",
            "preview_interac_summary_report",
            "preview_offerings_can_letter_report",
            "preview_interac_letter_report",
            "send_offerings_letter_receipt",
            "send_interac_letter_receipt",
            # Download and donor lookup endpoints. These were not listed in any
            # permission set previously, because the prefix was unchecked.
            "download_offerings_can_summary_report",
            "download_offerings_can_letter_report",
            "download_interac_summary_report",
            "download_interac_letter_receipts",
            "search-donor-names",
            "donations-receipt-list",
            "donation_receipt_preview",
        ]

        permissions["region_overseer"] = (
            permissions["local_church_pastor"] + receipt_permissions
        )
        permissions["national_overseer"] = (
            permissions["local_church_pastor"]
            + receipt_permissions
            + [
                "invite-users",
                "user_activate_deactivate",
                "user_list",
                "download_user_uploader_sample",
                "user_uploader",
            ]
        )
        return permissions[role]

    def check_permission(self, url_name, role):
        return url_name in self.role_based_permissions(role)

    def __call__(self, request):
        try:
            has_perm = False
            user = request.user

            if not user.is_anonymous:
                if user.role == Role.marriage_records.value:
                    url_name = resolve(request.path_info).url_name
                    has_perm = self.check_permission(url_name, "marriage_records")
                    if url_name == "dashboard":
                        return redirect('list_marriage_records')
                    if not has_perm:
                        return HttpResponseForbidden("Unauthorized: Access denied!")

            if request.path_info.split('/')[1] not in ["", "admin", "expense", "authentication", "income", "attendance", "member", "contributor"] or not re.match(r'^$|^[a-zA-Z0-9_-]+\?$', request.path_info.split('/')[1]):
                return self.get_response(request)
            print("request: ", request.path_info)
            url_name = resolve(request.path_info).url_name
            if user.is_anonymous:
                has_perm = self.check_permission(url_name, "public")
            else:
                if user.is_superuser:
                    has_perm = True
                elif user.role:
                    if user.role == Role.member.value:
                        has_perm = self.check_permission(url_name, "member")
                    elif user.role == Role.local_church_pastor.value:
                        has_perm = self.check_permission(url_name, "local_church_pastor")
                    elif user.role == Role.national_overseer.value:
                        has_perm = self.check_permission(url_name, "national_overseer")
                    elif user.role == Role.region_overseer.value:
                        has_perm = self.check_permission(url_name, "region_overseer")
                    else:
                        # Any role not handled above, including DONOR (6),
                        # falls back to member level rather than silently
                        # passing the request through unchecked.
                        has_perm = self.check_permission(url_name, "member")
                else:
                    has_perm = self.check_permission(url_name, "public")

            if not has_perm:
                return render(request, '403.html', status=403)
            else:
                return self.get_response(request)
        except Exception as e:
            traceback.print_exc()
            logger.error(str(e), stack_info=True)
            return render(request, '500.html', status=500)