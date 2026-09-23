# Create linked structure
To recreate the source directory structure while creating symbolic links to the
underlying files, use the following command
```
cp -rs source/ dest/
```

source must be an absolute path

## Example
For example, linking the nerdmobile files would use
```
cp -rs /uufs/chpc.utah.edu/common/home/lin-group15/MethaneAIR/data/nerdmobile/ .
```

# Update
```
cp -rsu source/ dest/
```

# Remove broken links
```
find -xtype l -delete
```
