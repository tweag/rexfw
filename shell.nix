{ pkgs ? import (fetchTarball https://github.com/NixOS/nixpkgs/archive/20.09.tar.gz) {} }:
with pkgs;
with pkgs.python38Packages;
pkgs.mkShell {
    buildInputs = [ poetry openmpi ];
  }
