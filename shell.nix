{ pkgs ? import (fetchTarball https://github.com/NixOS/nixpkgs/archive/20.09.tar.gz) {} }:
with pkgs;
with pkgs.python39Packages;
let 
  rexfw = buildPythonPackage rec {
    pname = "rexfw";
    version = "0.1.0";
    src = pkgs.lib.cleanSource ./.;
    doCheck = true;
    installCheckPhase = ''
      cd rexfw/test && python run_tests.py
    '';
    buildInputs = [ numpy ];
    propagatedBuildInputs = buildInputs ++ [ mpi4py openmpi ];
  };
in
  pkgs.mkShell {
    buildInputs = [ rexfw ];
  }
