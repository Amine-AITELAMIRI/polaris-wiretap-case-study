#include "Modem.hpp"

Modem::Modem(int n, CanalType canal, double param_canal) // Constructeur
  : Stateful() // Appel constructeur classe mère
  , n(n)
  , canal(canal)
  , param_canal(param_canal)
{
    const std::string name = "Modem"; // Donne un nom au module
    this->set_name(name); // this -> objet courant

    auto& p1 = this->create_task("modulate_BPSK");                                                  // Create the task
    size_t ps_input1 = this->template create_socket_in<double>(p1, "vect_encode", this->n);    // Create the input socket
    // uint8_t, ..., uint64_t
    // int8_t, ..., int64_t
    // float 
    // double
    // size_t ps_input = this->template create_socket_in<TYPE>(p, "NOM", TAILLE);    // Create the input socket

    size_t ps_output1 = this->template create_socket_out<double>(p1, "vect_module", this->n); // Create the output socket

    // create the codelet
    this->create_codelet(
      p1,
      [ps_input1, ps_output1](spu::module::Module& m, spu::runtime::Task& t, const size_t frame_id) -> int
      {
          // Recover the Module and Sockets in the codelet
          auto& modulate_BPSK = static_cast<Modem&>(m);
          double* vect_encode = (double*)(t[ps_input1].get_dataptr());
          double* vect_module = (double*)(t[ps_output1].get_dataptr());

          // Process the data
          modulate_BPSK.modulate_BPSK(vect_encode, vect_module);
          return spu::runtime::status_t::SUCCESS;
      });

    auto& p2 = this->create_task("demodulate_BPSK");                                                  // Create the task
    size_t ps_input2 = this->template create_socket_in<double>(p2, "vect_encode", this->n);    // Create the input socket
    // uint8_t, ..., uint64_t
    // int8_t, ..., int64_t
    // float 
    // double
    // size_t ps_input = this->template create_socket_in<TYPE>(p, "NOM", TAILLE);    // Create the input socket

    size_t ps_output2 = this->template create_socket_out<double>(p2, "vect_module", this->n); // Create the output socket

    // create the codelet
    this->create_codelet(
    p2,
    [ps_input2, ps_output2](spu::module::Module& m, spu::runtime::Task& t, const size_t frame_id) -> int
    {
        // Recover the Module and Sockets in the codelet
        auto& demodulate_BPSK = static_cast<Modem&>(m);
        double* vect_encode = (double*)(t[ps_input2].get_dataptr());
        double* vect_module = (double*)(t[ps_output2].get_dataptr());

        // Process the data
        demodulate_BPSK.demodulate_BPSK(vect_encode, vect_module);
        return spu::runtime::status_t::SUCCESS;
    });
}

// Implémentation des méthodes
std::vector<double> 
Modem::demoduler_bpsk_bsc(const std::vector<double>& signal_recu, double p) const
{
    std::vector<double> llrs(signal_recu.size());
    double factor = std::log((1.0 - p) / p);

    for (size_t i = 0; i < signal_recu.size(); ++i) {
        llrs[i] = signal_recu[i] * factor;
    }

    return llrs;
}

std::vector<double> 
Modem::demoduler_bpsk_awgn(const std::vector<double>& signal_recu, double snr_db) const
{
    size_t N = signal_recu.size();
    std::vector<double> llrs(N);

    // Calcul de sigma
    double sigma = std::sqrt(1.0 / (2.0 * std::pow(10.0, snr_db / 10.0)));

    for (size_t i = 0; i < N; ++i) {
        llrs[i] = (2.0 * signal_recu[i]) / sigma;
    }

    return llrs;
}

// Actual implementation of the task.
void
Modem::modulate_BPSK(const double* vect_encode, double* vect_module) const
{
    for (int i = 0; i < this->n ; i++)
        vect_module[i] = 1.0 - 2.0 * vect_encode[i];
}

void
Modem::demodulate_BPSK(const double* signal_recu, double* vect_llr) const
{
    // Wrap le pointeur brut en vector pour réutiliser les helpers
    const std::vector<double> signal(signal_recu, signal_recu + this->n);
    std::vector<double> llrs;

    switch (this->canal) {
        case CanalType::BSC:
            llrs = demoduler_bpsk_bsc(signal, this->param_canal);
            break;
        case CanalType::AWGN:
            llrs = demoduler_bpsk_awgn(signal, this->param_canal);
            break;
        default:
            throw std::invalid_argument("Type de canal non supporté");
    }

    // Copie le résultat vers le pointeur de sortie
    std::copy(llrs.begin(), llrs.end(), vect_llr);
}