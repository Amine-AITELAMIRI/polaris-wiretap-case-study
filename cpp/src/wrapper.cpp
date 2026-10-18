// Glue Python / C++

#include "Modem.hpp"
#include "Canal.hpp"
#include <pybind11/pybind11.h>
#include <streampu.hpp>
#include <pybind11/stl.h>        
#include <pybind11/operators.h>

namespace py = pybind11;
using namespace py::literals; // _a

// Create a	python module using PYBIND11, here our module will be named pyaf
PYBIND11_MODULE(my_module, m)
{
    auto pyspu_stateful = (py::object)py::module_::import("streampu"); // Pas toucher
    spu::tools::Buffer_allocator::set_task_autoalloc(true);
    m.attr("_spu") = pyspu_stateful; // Non plus

     // 1. Exposer l'enum CanalType côté Python
    py::enum_<Modem::CanalType>(m, "CanalType")
        .value("AWGN", Modem::CanalType::AWGN)
        .value("BSC",  Modem::CanalType::BSC)
        .export_values();

    // 2. Wrapper la classe avec le bon constructeur
    py::class_<Modem, spu::module::Stateful>(m, "Modem")
        .def(py::init<int, Modem::CanalType, double>(),
             "n"_a,
             "canal"_a,
             "param_canal"_a);
    
    // Ajouter le wrapper Canal
    py::class_<Canal, spu::module::Stateful>(m, "Canal")
        .def(py::init<int, Modem::CanalType, double, double, double>(),
             "n"_a,
             "type"_a,
             "param_canal"_a,
             "param_bob"_a,
             "param_eve"_a);
}
