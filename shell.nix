{ pkgs ? import (fetchTarball https://github.com/NixOS/nixpkgs/archive/20.09.tar.gz) {} }:
with pkgs;
with pkgs.python38Packages;
let 
  rexfw = buildPythonPackage rec {
    pname = "rexfw";
    version = "0.1.0";
    src = pkgs.lib.cleanSource ./.;
    buildInputs = [ numpy libcloud ];
    propagatedBuildInputs = buildInputs ++ [ mpi4py openmpi ];
  };
  resaas_lib = buildPythonPackage {
    pname = "resaas";
    version = "0.1.0";
    src = fetchGit {
      url = "git@github.com:tweag/resaas.git";
      rev = "TODO";
    };  
    buildInputs = [ numpy libcloud pyyaml ];
    propagatedBuildInputs = buildInputs;
  };
in
  pkgs.mkShell {
    buildInputs = [ rexfw ];
  }
