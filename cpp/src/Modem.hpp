#ifndef MODEM_HPP_
#define MODEM_HPP_
// Description de la classe

#include <streampu.hpp> // SPU

class Modem : public spu::module::Stateful // crée une classe qui hérite Stateful (classe de streampu <- Module)
{
  public:
    enum class CanalType {AWGN,BSC}; // Type de canal pour démod
  
  protected: // Attributs accessibles par les classes qui héritent de Adder
    int n;  // taille du vecteur
    CanalType canal;
    double param_canal; // valeur de snr_db si canal AWGN ou proba d'erreur si canal BSC
    
  public: // Accessible à tous
    Modem(int n, CanalType canal, double param_canal); // Constructeur 
    virtual ~Modem() = default; // Destructeur
 
    void modulate_BPSK(const double* input, double* output) const; // Méthode
    void demodulate_BPSK(const double* input, double* output) const; // Méthode

  private:
    std::vector<double> demoduler_bpsk_awgn(const std::vector<double>& signal_recu, double snr_db) const; // Méthode  
    std::vector<double> demoduler_bpsk_bsc(const std::vector<double>& signal_recu, double p) const; // Méthode

};

#endif // MODEM_HPP_