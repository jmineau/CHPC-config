# initialize R environment

# Set the path to user R library
R_SOFTWARE_DIR <- file.path(path.expand('~'), 'software', 'R')
source(file.path(R_SOFTWARE_DIR, 'user_library.r'))

# Get the list of installed packages
installed.pkgs <- rownames(utils::installed.packages())

# install packages
pkgs <- readLines(file.path(R_SOFTWARE_DIR, 'packages.txt'))
missing.pkgs <- pkgs[!pkgs %in% installed.pkgs]
if (length(missing.pkgs) > 0) {
  utils::install.packages(missing.pkgs, .libPaths()[1])
}

# install uataq package
if (!'uataq' %in% installed.pkgs) {
  if (!require('devtools')) utils::install.packages('devtools',
                                                    .libPaths()[1])
  devtools::install_github('uataq/uataq')
}