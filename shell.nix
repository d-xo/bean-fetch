let
  devEnv = (import ./default.nix).devEnv;
  pkgs = import (import ./nix/sources.nix).nixpkgs {};
in
pkgs.mkShell {
  buildInputs = with pkgs; [
    niv
    devEnv
    python3Packages.black
  ];
}
