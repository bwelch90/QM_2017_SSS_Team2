import numpy as np
import psi4

np.set_printoptions(suppress=True, precision=4)


def buildgeom:
    mol = psi4.geometry("""
    O
    H 1 1.1
    H 1 1.1 2 104
    """)

    # Build a molecule
    mol.update_geometry()
    mol.print_out()


    e_conv = 1.e-6
    d_conv = 1.e-6
    nel = 5
    damp_value = 0.20
    damp_start = 5
return mol 

# Build a basis
bas = psi4.core.BasisSet.build(mol,target="aug-cc-pvdz")
bas.print_out()

# Build a MintsHelper
mints = psi4.core.MintsHelper(bas)
nbf=mints.nbf()

if (nbf > 100):
   raise Exception("More than 100 basis functions!")

print(mints.ao_potential())

V = np.array(mints.ao_potential())
T = np.array(mints.ao_kinetic())

#Core Hamiltonian
H = T + V

S = np.array(mints.ao_overlap())
g = np.array(mints.ao_eri())

print(S.shape)
print(g.shape)


A = mints.ao_overlap()
A.power(-0.5, 1.e-14)
A = np.array(A)

# print(A @ S @ A)

def diag(F):
    Fp = A.T @ F @ A
    eps, Cp = np.linalg.eigh(Fp)
    C = A @ Cp
return eps, C

eps, C = diag(H)
Cocc = C[:, :nel]
D = Cocc @ Cocc.T



E_old = 0.0
F_old = H

def fock_build(D, damp=False):
    J = np.einsum("pqrs,rs->pq",g,D)
    K = np.einsum("prqs,rs->pq", g,D)
    F = H + 2.0 * J - K
    F_new = F
    if damp:
        F = damp_value * F_old + (1.0-damp_value) * F_new
    return F 

for iteration in range(25):
    F = fock_build(D, iteration>5) 

    #Build the AO Gradient
    grad = F @ D @ S - S @ D @ F      

    grad_rms = np.mean(grad ** 2) ** 0.5

    E_electric = np.sum((F+H) * D)
    E_total = E_electric + mol.nuclear_repulsion_energy()

    E_diff = E_total - E_old
    E_old = E_total

    print("Iter=%3d  E = % 16.12f  E_diff = % 8.4e  D_diff = % 8.4e" %
            (iteration, E_total, E_diff, grad_rms))

    #Break if e_conv and d_conv are met
    if (E_diff < e_conv) and (grad_rms < d_conv):
    break

    eps, C = diag(F, A)
    Cocc = C[:, :nel]
    D = Cocc @ Cocc.T

print("SCF has finished!\m")

psi4.set_options({"scf_type": "pk"})
psi4_energy = psi4.energy("SCF/aug-cc-pvdz", molecule=mol)
print("Energy matches Psi4 %s" % np.allclose(psi4_energy, E_total))



