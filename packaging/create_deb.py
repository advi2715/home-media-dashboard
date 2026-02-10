import sys
import os
import tarfile
import subprocess
import shutil

def main():
    if len(sys.argv) != 3:
        print("Usage: create_deb.py <build_dir> <output_deb>")
        sys.exit(1)

    build_dir = sys.argv[1]
    output_deb = os.path.abspath(sys.argv[2])
    
    # Paths
    debian_dir = os.path.join(build_dir, 'DEBIAN')
    if not os.path.exists(debian_dir):
        print(f"Error: DEBIAN directory not found in {build_dir}")
        sys.exit(1)

    # Temporary files
    temp_dir = os.path.join(build_dir, '.temp_deb')
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    try:
        # 1. debian-binary
        binary_path = os.path.join(temp_dir, 'debian-binary')
        with open(binary_path, 'w') as f:
            f.write("2.0\n")

        # 2. control.tar.gz
        print("Creating control.tar.gz...")
        control_tar_path = os.path.join(temp_dir, 'control.tar.gz')
        with tarfile.open(control_tar_path, "w:gz", format=tarfile.GNU_FORMAT) as tar:
            for root, dirs, files in os.walk(debian_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    # Rel path should be relative to DEBIAN, e.g. ./control
                    rel_path = os.path.relpath(full_path, debian_dir)
                    arcname = f"./{rel_path}"
                    
                    tar_info = tar.gettarinfo(full_path, arcname=arcname)
                    tar_info.uid = 0
                    tar_info.gid = 0
                    tar_info.uname = "root"
                    tar_info.gname = "root"
                    
                    if os.access(full_path, os.X_OK):
                        tar_info.mode = 0o755
                    else:
                        tar_info.mode = 0o644
                        
                    with open(full_path, "rb") as f:
                        tar.addfile(tar_info, f)

        # 3. data.tar.gz
        print("Creating data.tar.gz...")
        data_tar_path = os.path.join(temp_dir, 'data.tar.gz')
        with tarfile.open(data_tar_path, "w:gz", format=tarfile.GNU_FORMAT) as tar:
            # We want to add dirs and files that are NOT DEBIAN or .temp_deb
            # And structure them relative to build_dir, e.g. ./usr/bin/...
            
            # Pre-create ./ directory entry? Not strictly needed usually.
            
            for root, dirs, files in os.walk(build_dir):
                # Modify dirs in-place to skip
                if 'DEBIAN' in dirs:
                    dirs.remove('DEBIAN')
                if '.temp_deb' in dirs:
                    dirs.remove('.temp_deb')
                
                # Add current directory (if not build_dir root itself, though ./ is fine)
                rel_root = os.path.relpath(root, build_dir)
                if rel_root == '.':
                    arcname_root = '.'
                else:
                    arcname_root = f"./{rel_root}"
                
                # We typically don't add '.' explicitly unless needed, but ./usr is needed.
                # tarfile addfile for directory
                if rel_root != '.':
                     t_info = tar.gettarinfo(root, arcname=arcname_root)
                     t_info.uid = 0
                     t_info.gid = 0
                     t_info.uname = "root"
                     t_info.gname = "root"
                     t_info.mode = 0o755
                     tar.addfile(t_info)
                
                for f in files:
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, build_dir)
                    arcname = f"./{rel_path}"
                    
                    tar_info = tar.gettarinfo(full_path, arcname=arcname)
                    tar_info.uid = 0
                    tar_info.gid = 0
                    tar_info.uname = "root"
                    tar_info.gname = "root"
                    
                    # Inherit executable bit
                    if os.access(full_path, os.X_OK):
                        tar_info.mode = 0o755
                    else:
                        # Ensure secure permissions for /etc files?
                        # If file is in etc/, maybe 640?
                        # For now default to 644 unless it's the env file which we created.
                        # The original build script didn't create env file in build, only empty dir.
                        # So just standard 644/755.
                        tar_info.mode = 0o644

                    with open(full_path, "rb") as f:
                         tar.addfile(tar_info, f)

        # 4. Create .deb using ar
        print(f"Packaging into {output_deb}...")
        if os.path.exists(output_deb):
            os.remove(output_deb)
            
        # ar r creates archive.
        subprocess.check_call(['ar', 'rc', output_deb, 
                               binary_path,
                               control_tar_path,
                               data_tar_path])
        
        print("Done.")

    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == '__main__':
    main()
