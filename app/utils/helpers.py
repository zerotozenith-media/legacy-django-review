from django.utils.timezone import now

from organization.models import Region


def get_user_regions(user):
    try:
        if user.is_superuser or user.is_staff or user.role == 3:
            return Region.objects.all().order_by('name')
        elif user.role == 4:
            return Region.objects.filter(region_overseer=user).order_by('name')
        else:
            return []
    except Exception as e:
        print(f"Error fetching regions for user {user}: {e}")
        return []


def get_filtered_context(request, base_queryset, model_field_map):
    """
    Reusable filter logic for views.

    Args:
        request: HttpRequest
        base_queryset: initial queryset to filter
        model_field_map: dict mapping filter param to model field name

    Returns:
        tuple: (filtered_queryset, filter_context_dict)
    """
    filters = {}
    selected = {}

    for param, model_field in model_field_map.items():
        value = request.GET.get(param)
        if value:
            filters[model_field] = value
            selected[f"selected_{param}"] = value

    queryset = base_queryset.filter(**filters)

    # Optional year filter
    selected_year = request.GET.get("year")
    if selected_year:
        try:
            queryset = queryset.filter(created_date__year=int(selected_year))
            selected["selected_year"] = selected_year
        except Exception as e:
            print(e)
            pass

    # Year range context
    current_year = now().year
    selected["years"] = list(range(current_year, current_year - 5, -1))

    return queryset, selected
