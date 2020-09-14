let
  sources = import ./nix/sources.nix;
  pkgs = import sources.nixpkgs {};
  poetry2nix = import sources.poetry2nix { pkgs=pkgs; poetry=pkgs.poetry; };
  poetryOpts = { projectDir = ./.; };
in
{
  app = poetry2nix.mkPoetryApplication poetryOpts;
  devEnv = poetry2nix.mkPoetryEnv poetryOpts;
}

