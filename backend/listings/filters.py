from decimal import Decimal, InvalidOperation

from rest_framework.exceptions import ValidationError

from .models import Listing

def _decimal(params, name):
    raw = params.get(name)
    if raw is None or raw == '':
        return None
    try:
        value = Decimal(raw)
    except InvalidOperation:
        raise ValidationError({name: ['Має бути числом.']})
    if not value.is_finite() or value < 0:
        raise ValidationError({name: ['Має бути невід’ємним числом.']})
    return value


def _int(params, name):
    raw = params.get(name)
    if raw is None or raw == '':
        return None
    if not raw.isdigit():
        raise ValidationError({name: ['Має бути цілим невід’ємним числом.']})
    return int(raw)


def _check_range(name_min, name_max, low, high):
    if low is not None and high is not None and low > high:
        raise ValidationError({name_min: [f'Не може бути більшим за {name_max}.']})


def apply_listing_filters(qs, params):
    city = params.get('city', '').strip()
    if city:
        qs = qs.filter(city__iexact=city)

    district = params.get('district', '').strip()
    if district:
        qs = qs.filter(district__iexact=district)

    property_type = params.get('property_type')
    if property_type:
        if property_type not in Listing.PropertyType.values:
            allowed = ', '.join(Listing.PropertyType.values)
            raise ValidationError({'property_type': [f'Допустимі значення: {allowed}.']})
        qs = qs.filter(property_type=property_type)

    price_min, price_max = _decimal(params, 'price_min'), _decimal(params, 'price_max')
    _check_range('price_min', 'price_max', price_min, price_max)
    if price_min is not None:
        qs = qs.filter(price__gte=price_min)
    if price_max is not None:
        qs = qs.filter(price__lte=price_max)

    area_min, area_max = _decimal(params, 'area_min'), _decimal(params, 'area_max')
    _check_range('area_min', 'area_max', area_min, area_max)
    if area_min is not None:
        qs = qs.filter(area__gte=area_min)
    if area_max is not None:
        qs = qs.filter(area__lte=area_max)

    rooms, rooms_min = _int(params, 'rooms'), _int(params, 'rooms_min')
    if rooms is not None:
        qs = qs.filter(rooms=rooms)
    if rooms_min is not None:
        qs = qs.filter(rooms__gte=rooms_min)

    amenities = params.get('amenities', '')
    if amenities:
        ids = amenities.split(',')
        if not all(i.strip().isdigit() for i in ids):
            raise ValidationError({'amenities': ['Список id через кому, наприклад 1,3,4.']})
        for amenity_id in ids:
            qs = qs.filter(amenities__id=int(amenity_id))   # мають бути всі вибрані

    return qs