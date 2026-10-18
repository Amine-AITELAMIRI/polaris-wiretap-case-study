#ifndef CANAL_HPP_
#define CANAL_HPP_
// Description de la classe

#include <streampu.hpp> // SPU
#include <Modem.hpp>

class Canal : public spu::module::Stateful // crée une classe qui hérite Stateful (classe de streampu <- Module)
{
  protected: // Attributs accessibles par les classes qui héritent de Adder
    int n;
    Modem::CanalType type;
    double param_canal;
    double param_bob; // valeur de snr_db si canal AWGN ou proba d'erreur si canal BSC
    double param_eve;
    mutable std::mt19937 rng;

  public: // Accessible à tous
    Canal(int n, Modem::CanalType type, double param_canal, double param_bob, double param_eve);  // Constructeur  
                                           // & -> on passe par référence, donc pas de copie inutile, plus rapide.
    virtual ~Canal() = default; // Destructeur

    void canal_bsc(const double* input, double* output, double param_canal) const;
    void canal_awgn(const double* input, double* output, double param_canal) const;
    void canal(const double* input, double* signal_bob, double* signal_eve) const;
};

#endif // ENCODER_HPP_