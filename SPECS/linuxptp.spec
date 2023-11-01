%global _hardened_build 1
%global testsuite_ver c66922
%global clknetsim_ver c63e22

Name:		linuxptp
Version:	3.1.1
Release:	6%{?dist}.2
Summary:	PTP implementation for Linux

License:	GPLv2+
URL:		http://linuxptp.sourceforge.net/

Source0:	https://downloads.sourceforge.net/%{name}/%{name}-%{version}.tgz
Source1:	phc2sys.service
Source2:	ptp4l.service
Source3:	timemaster.service
Source4:	timemaster.conf
Source5:	ptp4l.conf
# external test suite
Source10:	https://github.com/mlichvar/linuxptp-testsuite/archive/%{testsuite_ver}/linuxptp-testsuite-%{testsuite_ver}.tar.gz
# simulator for test suite
Source11:	https://github.com/mlichvar/clknetsim/archive/%{clknetsim_ver}/clknetsim-%{clknetsim_ver}.tar.gz

# don't repeat some log messages in multi-port configuration
Patch1:		linuxptp-logmsgs.patch
# add option to set clockClass threshold
Patch2:		linuxptp-classthreshold.patch
# increase default TX timestamp timeout to 10 ms
Patch3:		linuxptp-deftxtout.patch
# limit unicast message rate per address and grant duration
Patch4:		linuxptp-ucastrate.patch
# add read-only UDS port
Patch5:		linuxptp-udsro.patch
# fix quoting in ptp4l man page
Patch7:		linuxptp-manfix.patch
# close lstab file after use
Patch8:		linuxptp-fclose.patch
# fix handling of zero-length messages
Patch9:		linuxptp-zerolength.patch
# avoid unaligned pointers to packed members
Patch10:	linuxptp-packalign.patch
# make sanity clock check more reliable
Patch11:	linuxptp-clockcheck.patch
# add support for virtual clocks
Patch12:	linuxptp-vclock.patch
# handle PHC read failing with EBUSY in phc2sys
Patch13:	linuxptp-phcerr.patch
# add support for VLAN over bond
Patch14:	linuxptp-vlanbond.patch
# handle EINTR when waiting for transmit timestamp
Patch15:	linuxptp-eintr.patch
# check for unexpected changes in frequency offset
Patch16:	linuxptp-freqcheck.patch
# don't re-arm fault clearing timer on unrelated netlink events
Patch17:	linuxptp-faultrearm.patch
# clear pending errors on sockets
Patch18:	linuxptp-soerror.patch

BuildRequires:	gcc gcc-c++ make systemd

%{?systemd_requires}

%description
This software is an implementation of the Precision Time Protocol (PTP)
according to IEEE standard 1588 for Linux. The dual design goals are to provide
a robust implementation of the standard and to use the most relevant and modern
Application Programming Interfaces (API) offered by the Linux kernel.
Supporting legacy APIs and other platforms is not a goal.

%prep
%setup -q -a 10 -a 11 -n %{name}-%{!?gitfullver:%{version}}%{?gitfullver}
%patch1 -p1 -b .logmsgs
%patch2 -p1 -b .classthreshold
%patch3 -p1 -b .deftxtout
%patch4 -p1 -b .ucastrate
%patch5 -p1 -b .udsro
%patch7 -p1 -b .manfix
%patch8 -p1 -b .fclose
%patch9 -p1 -b .zerolength
%patch10 -p1 -b .packalign
%patch11 -p1 -b .clockcheck
%patch12 -p1 -b .vclock
%patch13 -p1 -b .phcerr
%patch14 -p1 -b .vlanbond
%patch15 -p1 -b .eintr
%patch16 -p1 -b .freqcheck
%patch17 -p1 -b .faultrearm
%patch18 -p1 -b .soerror
mv linuxptp-testsuite-%{testsuite_ver}* testsuite
mv clknetsim-%{clknetsim_ver}* testsuite/clknetsim

%build
%{make_build} \
	EXTRA_CFLAGS="$RPM_OPT_FLAGS" \
	EXTRA_LDFLAGS="$RPM_LD_FLAGS"

%install
%makeinstall

mkdir -p $RPM_BUILD_ROOT{%{_sysconfdir}/sysconfig,%{_unitdir},%{_mandir}/man5}
install -m 644 -p %{SOURCE1} %{SOURCE2} %{SOURCE3} $RPM_BUILD_ROOT%{_unitdir}
install -m 644 -p %{SOURCE4} %{SOURCE5} $RPM_BUILD_ROOT%{_sysconfdir}

echo 'OPTIONS="-f /etc/ptp4l.conf"' > \
	$RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/ptp4l
echo 'OPTIONS="-a -r"' > $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/phc2sys

echo '.so man8/ptp4l.8' > $RPM_BUILD_ROOT%{_mandir}/man5/ptp4l.conf.5
echo '.so man8/timemaster.8' > $RPM_BUILD_ROOT%{_mandir}/man5/timemaster.conf.5

# Remove patch backup files and non-linuxptp configuration
find configs -type f ! -name '*.cfg' -delete

%check
cd testsuite
# set random seed to get deterministic results
export CLKNETSIM_RANDOM_SEED=26743
%{make_build} -C clknetsim
PATH=..:$PATH ./run

%post
%systemd_post phc2sys.service ptp4l.service timemaster.service

%preun
%systemd_preun phc2sys.service ptp4l.service timemaster.service

%postun
%systemd_postun_with_restart phc2sys.service ptp4l.service timemaster.service

%files
%doc COPYING README.org configs
%config(noreplace) %{_sysconfdir}/ptp4l.conf
%config(noreplace) %{_sysconfdir}/sysconfig/phc2sys
%config(noreplace) %{_sysconfdir}/sysconfig/ptp4l
%config(noreplace) %{_sysconfdir}/timemaster.conf
%{_unitdir}/phc2sys.service
%{_unitdir}/ptp4l.service
%{_unitdir}/timemaster.service
%{_sbindir}/hwstamp_ctl
%{_sbindir}/nsm
%{_sbindir}/phc2sys
%{_sbindir}/phc_ctl
%{_sbindir}/pmc
%{_sbindir}/ptp4l
%{_sbindir}/timemaster
%{_sbindir}/ts2phc
%{_mandir}/man5/*.5*
%{_mandir}/man8/*.8*

%changelog
* Thu May 18 2023 Miroslav Lichvar <mlichvar@redhat.com> 3.1.1-6.el9_2.2
- don't re-arm fault clearing timer on unrelated netlink events (#2208265)
- clear pending errors on sockets (#2208210)

* Mon Mar 20 2023 Miroslav Lichvar <mlichvar@redhat.com> 3.1.1-6.el9_2.1
- don't switch from system clock to PHC with SW timestamping (#2178233)

* Thu Jan 05 2023 Miroslav Lichvar <mlichvar@redhat.com> 3.1.1-6
- add support for VLAN over bond (#2120521)
- handle EINTR when waiting for transmit timestamp (#2128786)
- check for unexpected changes in frequency offset (#2150815)

* Thu Jul 28 2022 Miroslav Lichvar <mlichvar@redhat.com> 3.1.1-5
- disable PHC switch with vclocks (#2066452)

* Thu Jun 30 2022 Miroslav Lichvar <mlichvar@redhat.com> 3.1.1-4
- handle PHC read failing with EBUSY in phc2sys (#2102568)

* Thu Jun 09 2022 Miroslav Lichvar <mlichvar@redhat.com> 3.1.1-3
- add support for virtual clocks (#2067310)
- make sanity clock check more reliable (#2079893)

* Mon Aug 09 2021 Mohan Boddu <mboddu@redhat.com> - 3.1.1-2
- Rebuilt for IMA sigs, glibc 2.34, aarch64 flags
  Related: rhbz#1991688

* Mon Aug 02 2021 Miroslav Lichvar <mlichvar@redhat.com> 3.1.1-1
- update to 3.1.1 (#1979954 CVE-2021-3570 CVE-2021-3571)
- add read-only UDS port
- add option to set clockClass threshold
- don't repeat some log messages in multi-port configuration
- increase default TX timestamp timeout to 10 ms
- limit unicast message rate per address and grant duration

* Tue Jun 22 2021 Mohan Boddu <mboddu@redhat.com> - 3.1-5
- Rebuilt for RHEL 9 BETA for openssl 3.0
  Related: rhbz#1971065

* Fri Apr 16 2021 Mohan Boddu <mboddu@redhat.com> - 3.1-4
- Rebuilt for RHEL 9 BETA on Apr 15th 2021. Related: rhbz#1947937

* Thu Feb 25 2021 Miroslav Lichvar <mlichvar@redhat.com> 3.1-3
- fix handling of zero-length messages
- minimize default configuration
- remove obsolete build requirement

* Tue Jan 26 2021 Fedora Release Engineering <releng@fedoraproject.org> - 3.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Tue Sep 29 2020 Miroslav Lichvar <mlichvar@redhat.com> 3.1-1
- update to 3.1

* Mon Jul 27 2020 Miroslav Lichvar <mlichvar@redhat.com> 3.0-1
- update to 3.0

* Mon Feb 03 2020 Miroslav Lichvar <mlichvar@redhat.com> 2.0-7.20191225gite05809
- update to 20191225gite05809
- fix testing with new glibc

* Wed Jan 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 2.0-6.20190912git48e605
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Wed Sep 25 2019 Miroslav Lichvar <mlichvar@redhat.com> 2.0-5.20190912git48e605
- update to 20190912git48e605

* Thu Jul 25 2019 Fedora Release Engineering <releng@fedoraproject.org> - 2.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Fri Feb 01 2019 Fedora Release Engineering <releng@fedoraproject.org> - 2.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Tue Nov 13 2018 Miroslav Lichvar <mlichvar@redhat.com> 2.0-2
- start ptp4l, timemaster and phc2sys after network-online target
- fix building with new kernel headers

* Mon Aug 13 2018 Miroslav Lichvar <mlichvar@redhat.com> 2.0-1
- update to 2.0

* Thu Aug 09 2018 Miroslav Lichvar <mlichvar@redhat.com> 2.0-0.1.20180805gita27407
- update to 20180805gita27407

* Mon Jul 16 2018 Miroslav Lichvar <mlichvar@redhat.com> 1.9.2-3
- add gcc and gcc-c++ to build requirements

* Fri Jul 13 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.9.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Mon Apr 09 2018 Miroslav Lichvar <mlichvar@redhat.com> 1.9.2-1
- update to 1.9.2

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.8-7.20180101git303b08
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Tue Jan 30 2018 Miroslav Lichvar <mlichvar@redhat.com> 1.8-6.20180101git303b08
- use macro for systemd scriptlet dependencies

* Thu Jan 11 2018 Miroslav Lichvar <mlichvar@redhat.com> 1.8-5.20180101git303b08
- update to 20180101git303b08

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.8-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.8-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.8-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Mon Nov 07 2016 Miroslav Lichvar <mlichvar@redhat.com> 1.8-1
- update to 1.8

* Fri Jul 22 2016 Miroslav Lichvar <mlichvar@redhat.com> 1.7-1
- update to 1.7
- add delay option to default timemaster.conf

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1.6-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Tue Sep 22 2015 Miroslav Lichvar <mlichvar@redhat.com> 1.6-1
- update to 1.6
- set random seed in testing to get deterministic results
- remove trailing whitespace in default timemaster.conf

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Mon Jan 05 2015 Miroslav Lichvar <mlichvar@redhat.com> 1.5-1
- update to 1.5

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Fri Feb 21 2014 Miroslav Lichvar <mlichvar@redhat.com> 1.4-1
- update to 1.4
- replace hardening build flags with _hardened_build
- include test suite

* Fri Aug 02 2013 Miroslav Lichvar <mlichvar@redhat.com> 1.3-1
- update to 1.3

* Tue Jul 30 2013 Miroslav Lichvar <mlichvar@redhat.com> 1.2-3.20130730git7789f0
- update to 20130730git7789f0

* Fri Jul 19 2013 Miroslav Lichvar <mlichvar@redhat.com> 1.2-2.20130719git46db40
- update to 20130719git46db40
- drop old systemd scriptlets
- add man page link for ptp4l.conf

* Mon Apr 22 2013 Miroslav Lichvar <mlichvar@redhat.com> 1.2-1
- update to 1.2

* Mon Feb 18 2013 Miroslav Lichvar <mlichvar@redhat.com> 1.1-1
- update to 1.1
- log phc2sys output

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Thu Dec 13 2012 Miroslav Lichvar <mlichvar@redhat.com> 1.0-1
- update to 1.0

* Fri Nov 09 2012 Miroslav Lichvar <mlichvar@redhat.com> 0-0.3.20121109git4e8107
- update to 20121109git4e8107
- install unchanged default.cfg as ptp4l.conf
- drop conflicts from phc2sys service

* Fri Sep 21 2012 Miroslav Lichvar <mlichvar@redhat.com> 0-0.2.20120920git6ce135
- fix issues found in package review (#859193)

* Thu Sep 20 2012 Miroslav Lichvar <mlichvar@redhat.com> 0-0.1.20120920git6ce135
- initial release
