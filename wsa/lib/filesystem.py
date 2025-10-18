import os


class ComparePaths:
    UPLOAD_MISSING = 1
    UPDATE = 2
    UPLOAD_ALL = UPLOAD_MISSING + UPDATE
    DELETE = 4

    @staticmethod
    def full_walk(walk_iterator) -> tuple[list[str], list[str]]:
        fp_root = None
        fp_dirs = []
        fp_files = []
        for root, dirs, files in walk_iterator:
            if fp_root is None:
                fp_root = root
            path = root[len(fp_root):].lstrip("/")
            for file in files:
                fp_files.append(f"{path}/{file}")
            for dir in dirs:
                fp_dirs.append(f"{path}/{file}")
        return (fp_root, fp_dirs, fp_files)

    def __init__(self, local_path: str, remote_client, remote_path: str = None):
        self.local_path = local_path
        self.remote_client = remote_client
        self.remote_path = remote_path
        self.compare()

    def compare(self):
        self.local_root, self.local_dirs, self.local_files = ComparePaths.full_walk(os.walk(self.local_path))
        self.remote_root, self.remote_dirs, self.remote_files = ComparePaths.full_walk(self.remote_client.walk(self.remote_path))
        print(self.local_root, "vs", self.remote_root)
        self.missing_remotely = set(self.local_files) - set(self.remote_files)
        self.to_remove_remotely = set(self.remote_files) - set(self.local_files)
        self.both = set(self.local_files) & set(self.remote_files)

    def upload(self, file):
        print("UPLOAD", file)

    def sync(self, mode:int=None):
        if mode is None:
            mode = ComparePaths.UPLOAD_ALL
        if mode & ComparePaths.UPLOAD_MISSING:
            for file in self.missing_remotely:
                self.upload(file)
        if mode & ComparePaths.UPDATE:
            for file in self.both:
                self.upload(file)
