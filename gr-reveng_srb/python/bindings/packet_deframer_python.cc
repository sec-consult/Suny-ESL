/*
 * Copyright 2021 Free Software Foundation, Inc.
 *
 * This file is part of GNU Radio
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 */

/***********************************************************************************/
/* This file is automatically generated using bindtool and can be manually edited  */
/* The following lines can be configured to regenerate this file during cmake      */
/* If manual edits are made, the following tags should be modified accordingly.    */
/* BINDTOOL_GEN_AUTOMATIC(1)                                                       */
/* BINDTOOL_USE_PYGCCXML(0)                                                        */
/* BINDTOOL_HEADER_FILE(packet_deframer.h)                                        */
/* BINDTOOL_HEADER_FILE_HASH(0203640b2d76742345a4cdb7eca35de2)                     */
/***********************************************************************************/

#include <pybind11/complex.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

#include <reveng_srb/packet_deframer.h>
// pydoc.h is automatically generated in the build directory
#include <packet_deframer_pydoc.h>

void bind_packet_deframer(py::module& m)
{

    using packet_deframer    = gr::reveng_srb::packet_deframer;


    py::class_<packet_deframer, gr::sync_block, gr::block, gr::basic_block,
        std::shared_ptr<packet_deframer>>(m, "packet_deframer", D(packet_deframer))

        .def(py::init(&packet_deframer::make),
           py::arg("name"),
           py::arg("sync"),
           py::arg("fixed_len"),
           py::arg("pkt_len"),
           py::arg("max_len"),
           py::arg("pkt_len_offset"),
           py::arg("pkt_len_adj"),
           py::arg("pack_bytes"),
           D(packet_deframer,make)
        )
        



        ;




}







