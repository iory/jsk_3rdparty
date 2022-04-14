# -*- makefile -*-

all: installed.rnnoise

SHA = 1cbdbcf1283499bbb2230a6b0f126eb9b236defd
FILENAME = rnnoise-$(SHA).tar.gz
TARBALL = build/${FILENAME}
TARBALL_URL = https://github.com/xiph/rnnoise/archive/1cbdbcf1283499bbb2230a6b0f126eb9b236defd.tar.gz
SOURCE_DIR = build/rnnoise-${SHA}
MD5SUM_DIR = $(CURDIR)/md5sum
MD5SUM_FILE = $(MD5SUM_DIR)/$(FILENAME).md5sum
UNPACK_CMD = tar xzf
include $(shell rospack find mk)/download_unpack_build.mk
INSTALL_DIR = `rospack find rnnoise`

installed.rnnoise: $(SOURCE_DIR)/unpacked
	(cd $(SOURCE_DIR) && ./autogen.sh; ./configure --prefix=$(INSTALL_DIR); make; make install)
	touch installed.rnnoise
clean:
	rm -rf $(TARBALL)
	rm -rf $(SOURCE_DIR)
	rm -rf $(INSTALL_DIR)/build
	rm -rf $(INSTALL_DIR)/include
	rm -rf $(INSTALL_DIR)/lib
	rm -rf $(INSTALL_DIR)/share
	rm -rf installed.rnnoise
