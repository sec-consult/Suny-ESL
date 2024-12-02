if(NOT PKG_CONFIG_FOUND)
    INCLUDE(FindPkgConfig)
endif()
PKG_CHECK_MODULES(PC_REVENG_SRB reveng_srb)

FIND_PATH(
    REVENG_SRB_INCLUDE_DIRS
    NAMES reveng_srb/api.h
    HINTS $ENV{REVENG_SRB_DIR}/include
        ${PC_REVENG_SRB_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    REVENG_SRB_LIBRARIES
    NAMES gnuradio-reveng_srb
    HINTS $ENV{REVENG_SRB_DIR}/lib
        ${PC_REVENG_SRB_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/reveng_srbTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(REVENG_SRB DEFAULT_MSG REVENG_SRB_LIBRARIES REVENG_SRB_INCLUDE_DIRS)
MARK_AS_ADVANCED(REVENG_SRB_LIBRARIES REVENG_SRB_INCLUDE_DIRS)
