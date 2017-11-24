from tastypie.authorization import Authorization, DjangoAuthorization


class ExtendedDjangoAuthorization(DjangoAuthorization):
    def read_list(self, object_list, bundle):
        return Authorization.read_list(self, object_list, bundle)

    def read_detail(self, object_list, bundle):
        return Authorization.read_detail(self, object_list, bundle)
