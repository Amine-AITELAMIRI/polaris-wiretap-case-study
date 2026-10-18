#include "Canal.hpp"
#include "Modem.hpp"

Canal::Canal(int n, Modem::CanalType type, double param_bob, double param_eve, double param_canal) // Constructeur
  : Stateful() // Appel constructeur classe mère
  , n(n)
  , type(type)
  , param_canal(param_canal)
  , param_bob(param_bob)
  , param_eve(param_eve)
  , rng(std::random_device{}())
{
    const std::string name = "Canal"; // Donne un nom au module
    this->set_name(name); // this -> objet courant

    auto& p1 = this->create_task("canal");                                                  // Create the task
    size_t ps_input1 = this->template create_socket_in<double>(p1, "vect_encode", this->n);    // Create the input socket
    // uint8_t, ..., uint64_t
    // int8_t, ..., int64_t
    // float 
    // double
    // size_t ps_input = this->template create_socket_in<TYPE>(p, "NOM", TAILLE);    // Create the input socket

    size_t ps_output1 = this->template create_socket_out<double>(p1, "vect_bob", this->n); // Create the output socket
    size_t ps_output2 = this->template create_socket_out<double>(p1, "vect_eve", this->n);

    // create the codelet
    this->create_codelet(
      p1,
      [ps_input1, ps_output1, ps_output2](spu::module::Module& m, spu::runtime::Task& t, const size_t frame_id) -> int
      {
          // Recover the Module and Sockets in the codelet
          auto& canal = static_cast<Canal&>(m);
          double* vect_encode = (double*)(t[ps_input1].get_dataptr());
          double* vect_bob = (double*)(t[ps_output1].get_dataptr());
          double* vect_eve = (double*)(t[ps_output2].get_dataptr());

          // Process the data
          canal.canal(vect_encode, vect_bob, vect_eve);
          return spu::runtime::status_t::SUCCESS;
      });

}

// Implémentation des méthodes
void Canal::canal_bsc(const double* input, double* output, double param_canal) const
{
    std::uniform_real_distribution<double> dist(0.0, 1.0);

    for (int i = 0; i < this->n; i++)
        output[i] = input[i] * (dist(this->rng) < param_canal ? -1.0 : 1.0);
}

void Canal::canal_awgn(const double* input, double* output, double param_canal) const
{
    const double sigma = std::sqrt(1.0 / (2.0 * std::pow(10.0, param_canal / 10.0)));

    std::normal_distribution<double> dist(0.0, sigma);

    for (int i = 0; i < this->n; i++)
        output[i] = input[i] + dist(this->rng);
}

void Canal::canal(const double* input, double* signal_bob, double* signal_eve) const
{
    switch (this->type)
    {
        case Modem::CanalType::BSC:
            canal_bsc(input, signal_bob, this->param_bob);
            canal_bsc(input, signal_eve, this->param_eve);
            break;

        case Modem::CanalType::AWGN:
            canal_awgn(input, signal_bob, this->param_bob);
            canal_awgn(input, signal_eve, this->param_eve);
            break;
    }
}
