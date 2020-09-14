let
  sources = import ./nix/sources.nix;
  pkgs = import sources.nixpkgs {};
  poetry2nix = import sources.poetry2nix { pkgs=pkgs; poetry=pkgs.poetry; };

  poetryOpts = {
    projectDir = ./.;
    overrides = poetry2nix.overrides.withDefaults (self: super: {
      eth-hash = super.eth-hash.overridePythonAttrs (old: {
        preConfigure = ''
          substituteInPlace setup.py --replace \'setuptools-markdown\' ""
        '';
      });
      eth-keyfile = super.eth-keyfile.overridePythonAttrs (old: {
        preConfigure = ''
          substituteInPlace setup.py --replace \'setuptools-markdown\' ""
        '';
      });
      eth-keys = super.eth-keys.overridePythonAttrs (old: {
        preConfigure = ''
          substituteInPlace setup.py --replace \'setuptools-markdown\' ""
        '';
      });
      rlp = super.rlp.overridePythonAttrs (old: {
        preConfigure = ''
          substituteInPlace setup.py --replace \'setuptools-markdown\' ""
        '';
      });
      web3 = super.web3.overridePythonAttrs (old: {
        preConfigure = ''
          substituteInPlace setup.py --replace \'setuptools-markdown\' ""
        '';
      });
      multiaddr = super.multiaddr.overridePythonAttrs (old: {
        buildInputs = old.buildInputs ++ [ self.pytest-runner ];
      });
      jsonpickle = super.jsonpickle.overridePythonAttrs (old: {
        dontPreferSetupPy = true;
      });
    });
  };
in
{
  app = poetry2nix.mkPoetryApplication poetryOpts;
  dev-env = poetry2nix.mkPoetryEnv (poetryOpts // {
    editablePackageSources = {
      bean-fetch = ./bean_fetch;
    };
  });
}

