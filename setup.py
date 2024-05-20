from cx_Freeze import setup, Executable


# Укажите файлы и папки, которые необходимо включить в сборку
include_files = [
    ("icons", "icons")  # Копировать папку resources
]

setup(
    name="YourAppName",
    version="0.1",
    description="Описание вашего приложения",
    options={
        "build_exe": {
            "include_files": include_files
        }
    },
    executables=[Executable("main.py")]
)
