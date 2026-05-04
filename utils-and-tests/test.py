import contador_instancias as ci
import contador_repetidos as cr

file = "Alunos CC e SI-NORMALIZADO.csv"

print(ci.headers(file))
# print(ci.unique_values(file, 18))
print(ci.value_counts(file, 8)["CIENCIA DA COMPUTACAO - BACHARELADO"])
print(ci.value_counts(file, 8)["BACHARELADO EM SISTEMAS DE INFORMACAO"])
print(ci.value_counts(file, 8)["CIENCIA DA COMPUTACAO - BACHARELADO"] + ci.value_counts(file, 8)["BACHARELADO EM SISTEMAS DE INFORMACAO"])
print(ci.value_counts(file, 18)["NAN"])

print(cr.repeated_values(file, 8))
print(cr.total_repeated_rows(file, 8))
print(cr.total_repeated_rows(file, 0))