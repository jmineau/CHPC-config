# Get R version
R_MAJOR_VERSION <- paste(c(
  R.version$major,
  strsplit(R.version$minor, '\\.')[[1]][1]),
  collapse = '.')

# Set the path to user R library
R_LIBS_USER <- file.path(path.expand('~'), 'software', 'R', 
                         R_MAJOR_VERSION)
# Create directory if it doesn't exist
if (!dir.exists(R_LIBS_USER)) {
  dir.create(R_LIBS_USER, recursive = TRUE)
}
.libPaths(R_LIBS_USER)
rm(R_MAJOR_VERSION, R_LIBS_USER)
