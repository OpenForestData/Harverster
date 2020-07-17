import datetime

import factory

from django.utils import timezone

from core.models import ResourceMapping


class ResourceMappingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ResourceMapping

    uid = factory.Faker('uuid4')
    created_at = factory.LazyAttribute(lambda o: o.now - datetime.timedelta(minutes=10))
    last_update = factory.LazyFunction(timezone.now)
    category = ResourceMapping.DASHBOARD
