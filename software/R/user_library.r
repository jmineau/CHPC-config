# Set the path to R user library

# Get the path to R software directory
R_SOFTWARE_DIR <- file.path(path.expand('~'), 'software', 'R')

# Get R version
R_MAJOR_VERSION <- paste(c(
  R.version$major,
  strsplit(R.version$minor, '\\.')[[1]][1]),
  collapse = '.')

# Get the path to user library
R_LIBS_USER <- file.path(R_SOFTWARE_DIR, R_MAJOR_VERSION)

# Create directory if it doesn't exist
if (!dir.exists(R_LIBS_USER)) {
  dir.create(R_LIBS_USER, recursive = TRUE)
}

# Add user library to R lib paths
.libPaths(R_LIBS_USER)
