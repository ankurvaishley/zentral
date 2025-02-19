import os
from zentral.utils.osx_package import EnrollmentPackageBuilder
from zentral.contrib.osquery.forms import EnrollmentForm
from zentral.contrib.osquery.releases import get_osquery_local_asset

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class OsqueryZentralEnrollPkgBuilder(EnrollmentPackageBuilder):
    name = "Zentral Osquery Enrollment"
    package_name = "zentral_osquery_enroll.pkg"
    base_package_identifier = "io.zentral.osquery_enroll"
    build_tmpl_dir = os.path.join(BASE_DIR, "build.tmpl")
    form = EnrollmentForm
    standalone = True

    def __init__(self, enrollment, version=None):
        super().__init__(enrollment, version,
                         release=enrollment.osquery_release,
                         serialized_flags=enrollment.configuration.get_serialized_flags())

    def get_product_archive_title(self):
        return self.name

    def get_extra_packages(self):
        extra_packages = []
        release = self.build_kwargs.get("release")
        if release:
            extra_packages.append(get_osquery_local_asset(release, ".pkg"))
        return extra_packages

    def extra_build_steps(self):
        # enroll secret secret in preinstall
        self.replace_in_file(self.get_build_path("scripts", "preinstall"),
                             (("%ENROLL_SECRET_SECRET%", self.build_kwargs["enrollment_secret_secret"]),))

        # tls_hostname in postinstall
        hostname_replacement = (("%TLS_HOSTNAME%", self.get_tls_hostname()),)
        self.replace_in_file(self.get_build_path("scripts", "postinstall"), hostname_replacement)

        # Launch daemon extra ProgramArguments
        extra_prog_args = self.build_kwargs["serialized_flags"]

        # include the certs and point to them in the ProgramArguments if necessary
        tls_server_certs_install_path = self.include_tls_server_certs()
        if tls_server_certs_install_path:
            extra_prog_args.append("--tls_server_certs={}".format(tls_server_certs_install_path))
        launchd_plist = self.get_root_path("Library/LaunchDaemons/com.facebook.osqueryd.plist")

        # add the extra prog args in the plist
        self.append_to_plist_key(launchd_plist, "ProgramArguments", extra_prog_args)
