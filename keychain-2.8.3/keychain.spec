Name:      keychain
Version:   2.8.3
Release:   1
Summary:   agent manager for OpenSSH, ssh.com, Sun SSH, and GnuPG
Packager:  Daniel Robbins <drobbins@funtoo.org>
URL:       http://www.funtoo.org 
Source0:   %{name}-%{version}.tar.bz2
License:   GPL v2
Group:     Applications/Internet
BuildArch: noarch
Requires:  /bin/sh sh-utils
Prefix:    /usr/bin
BuildRoot: %{_tmppath}/%{name}-root

%description
Keychain is a manager for OpenSSH, ssh.com, Sun SSH and GnuPG agents.
It acts as a front-end to the agents, allowing you to easily have one
long-running agent process per system, rather than per login session.
This reduces the number of times you need to enter your passphrase
from once per new login session to once every time your local machine
is rebooted.

%prep
%setup -q

%build

%install
[ $RPM_BUILD_ROOT != / ] && rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/%{_bindir} $RPM_BUILD_ROOT/%{_mandir}/man1
install -m0755 keychain $RPM_BUILD_ROOT/%{_bindir}/keychain
install -m0644 keychain.1 $RPM_BUILD_ROOT/%{_mandir}/man1

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
     %{_bindir}/*
%doc %{_mandir}/*/*
%doc ChangeLog COPYING.txt keychain.pod README.md
