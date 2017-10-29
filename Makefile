PREFIX ?= /usr/local
DESTDIR ?=
BINDIR ?= $(PREFIX)/bin
SHAREDIR ?= $(PREFIX)/share/very-scary
BINFILE = bin/very-scary.py
SOUNDFILE = share/very-scary/Scream.mp3

UNITFILE = very-scary.service

all:
	@printf "To install run: sudo make install\nTo run at startup run: sudo make enable\n"

install:
	@install -d "$(DESDIR)$(BINDIR)"
	@install -d "$(DESDIR)$(SHAREDIR)"
	@install -m 0755 "$(BINFILE)" "$(DESTDIR)$(BINDIR)/very-scary"
	@install -m 0644 "$(SOUNDFILE)" "$(DESTDIR)$(SHAREDIR)/Scream.mp3"

enable:
	@install -m 0644 "$(UNITFILE)" "/etc/systemd/system/very-scary.service"
	systemctl daemon-reload
	systemctl enable very-scary.service

disable:
	@systemctl disable very-scary
	@rm -f "/etc/systemd/system/very-scary.service"

uninstall:
	@rm -f "$(DESTDIR)$(BINDIR)/very-scary"
	@rm -f "$(DESTDIR)$(SHAREDIR)/Scream.mp3"

.PHONY: install uninstall
