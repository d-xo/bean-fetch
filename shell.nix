{ nixpkgs ? <nixpkgs> }:

let
  pkgs = import nixpkgs {};
in
  pkgs.mkShell {
    buildInputs = with pkgs; [
      libxml2
      libxslt
      openssl
      mypy
      python37
      python37Packages.poetry
      python37Packages.black
      python37Packages.python-language-server
    ];
}
