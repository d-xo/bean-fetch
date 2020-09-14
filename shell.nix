let
  app = (import ./default.nix).dev-env;
  pkgs = import (import ./nix/sources.nix).nixpkgs {};
in pkgs.mkShell {
  buildInputs = [
    app
  ];
}
