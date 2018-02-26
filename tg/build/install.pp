
$packages = [
	"gcc", "cpp", "make", "pkg-config", "flex", "bison",
	"libnacl-dev", "libz-dev", "libncurses5-dev", "libnl-3-dev"
]

package { $packages: ensure => installed }

