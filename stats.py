import csv
import re

def procesar_log(log_path, output_csv):
    columns = [
        "Archivo",
        "Funcionalidad",
        "Tipo de Error",
        "Línea",
        "Mensaje de Error",
        "Responsable",
        "Fecha de Registro",
        "Estado",
        "Notas Adicionales"
    ]

    with open(output_csv, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)

        writer.writeheader()

        current_path = None
        current_file = None
        current_functionality = None
        current_error_type = None
        current_error_line = None
        current_error_message = None
        i = 0

        with open(log_path, "r") as file:
            file = [line.rstrip() for line in file.readlines()]

            for line in file:
                if re.search(r'(\/[\w-]*\.js)', line):
                    current_file = re.search(r'(\/[\w-]*\.js)', line).group(1)
                    current_path = line
                    current_functionality = None
                    current_error_type = None
                    current_error_line = None
                    current_error_message = None
                elif not line.endswith(".js") and line:
                    parts = line.split()
                    current_error_type = parts[-1]
                    current_error_line = int(parts[0].split(':')[0])
                    current_error_message = ' '.join(parts[2:-1])
                    functionality = current_file.split('.')[0].replace("/", "")
                    readable_string = ""
                    for char in functionality:
                        if char.isupper():
                            readable_string += " "
                        readable_string += char

                    readable_string = readable_string.split(" ")
                    readable_string = [word.capitalize() for word in readable_string]

                    current_functionality = " ".join(readable_string)
  

                    writer.writerow({
                        "Archivo": current_path,
                        "Funcionalidad": current_functionality,
                        "Tipo de Error": current_error_type,
                        "Línea": current_error_line,
                        "Mensaje de Error": current_error_message,
                        "Responsable": "",
                        "Fecha de Registro": "",
                        "Estado": "",
                        "Notas Adicionales": ""
                    })


procesar_log("lintdocumentacion", "output.csv")
