Name:   tmate-slave
Version:  20160616
Release:  1%{?dist}
Summary:  tmate slave server

#Group:
License:  MIT
URL:    https://github.com/tmate-io/tmate-slave
Source0:  %{name}-master.zip
Source1:  %{name}.service
Source2:  %{name}.sysconfig
BuildRoot:  %{name}-%{version}-%{buildarch}
BuildArch:  x86_64

BuildRequires:    libevent-devel libssh-devel kernel-devel msgpack-devel ncurses-devel openssl-devel zlib-devel
BuildRequires:    cmake systemd
Requires:         msgpack libssh
Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd

%description
tmate-slave is the server side part of tmate.io.

%prep
%setup -q -n tmate-slave-master
cp -p %SOURCE1 .
cp -p %SOURCE2 .



%build
./autogen.sh
%configure
make %{?_smp_mflags}


%install
rm -rf %{buildroot}
%make_install
mkdir -p %{buildroot}%{_sysconfdir}/sysconfig/
cp tmate-slave.sysconfig %{buildroot}%{_sysconfdir}/sysconfig/tmate-slave
mkdir -p %{buildroot}/usr/lib/systemd/system
cp tmate-slave.service %{buildroot}/usr/lib/systemd/system/
mkdir %{buildroot}%{_sysconfdir}/tmate-slave

%files
%defattr(-,root,root,-)
%doc create_keys.sh
%{_bindir}/tmate-slave
/usr/lib/systemd/system/tmate-slave.service
%config %{_sysconfdir}/sysconfig/tmate-slave
%{_sysconfdir}/tmate-slave/

%post
if [ $1 -eq 1 ]; then
  # initial install
  CONF="/etc/tmate-slave/tmate.conf.sample"
  touch ${CONF}
  mkdir -p /etc/tmate-slave/keys
  for type in dsa rsa ecdsa; do
    if [ ! -f /etc/tmate-slave/keys/ssh_host_${type}_key ]; then
      ssh-keygen -t ${type} -f /etc/tmate-slave/keys/ssh_host_${type}_key -N '' &>/dev/null
      FP=$(ssh-keygen -l -f /etc/tmate-slave/keys/ssh_host_${type}_key | awk '{print $2}')
      echo set -g "tmate-server-${type}-fingerprint" "${FP}" >> "${CONF}"
    fi
  done
  grep -q tmate-server-host $CONF || echo set -g tmate-server-host "${HOSTNAME}" >> "${CONF}"
  grep -q tmate-server-port $CONF || echo set -g tmate-server-port 22000 >> "${CONF}"
  systemctl preset tmate-slave.service >/dev/null 2>&1 || :
fi
if [ $1 -gt 1 ]; then
  %systemd_post tmate-slave.service
fi

%preun
if [ $1 -eq 0 ] ; then
  # removal, not upgrade
  systemctl --no-reload disable tmate-slave.service > /dev/null 2>&1 || :
  systemctl stop tmate-slave.service > /dev/null 2>&1 || :
fi

%postun
systemctl daemon-reload >/dev/null 2>&1 || :

%changelog
* Thu Jun 16 2016 Scott Merrill <skippy@skippy.net> - 20160616-1
- remove Ruby from BuildRequires. It's not required for building.
* Mon May 16 2016 Scott Merrill <skippy@skippy.net> - 20160426-1
- use latest upstream code
- create /etc/tmate-slave/tmate.conf.sample in post script with client-ready content
* Fri Jan 15 2016 Scott Merrill <skippy@skippy.net> - 20160105-1
- rebuild using latest master code
- remove logrotate file, and log option from sysconfig file
* Thu Apr 23 2015 Scott Merrill <skippy@skippy.net> - 1.8-2
- add logrotate, sysconfig, and systemd files
- add post script to ensure creation of keys and sample client config
* Wed Apr 15 2015 Scott Merrill <skippy@skippy.net> - 1.8-1
- initial RPM build
