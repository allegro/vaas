from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.http import HttpResponseRedirect

from vaas.cluster.cluster import ServerExtractor
from vaas.cluster.models import LogicalCluster
from .forms import PurgeForm
from vaas.purger.purger import VarnishPurger


def purger_permission(user):
    return user.is_staff


@user_passes_test(purger_permission, login_url="/admin/login")
def purge_view(request):
    if request.method == "POST":
        form = PurgeForm(request.POST)
        if form.is_valid():
            cluster = LogicalCluster.objects.get(pk=form.cleaned_data["cluster"].pk)
            servers = ServerExtractor().extract_servers_by_clusters([cluster])
            result = VarnishPurger().purge_url(form.cleaned_data["url"], servers)
            messages.warning(
                request,
                "Url {} purged from cluster {} - cleaned {} server(s), errors occurred for {} server(s)".format(
                    form.cleaned_data["url"],
                    cluster.name,
                    len(result["success"]),
                    len(result["error"]),
                ),
            )
            return HttpResponseRedirect("/")
    else:
        form = PurgeForm()

    context = {"form": form, "has_permission": True}
    context.update(admin.site.each_context(request))

    return render(request, "purge_form.html", context)
