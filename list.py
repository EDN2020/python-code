# opening the file in read mode
my_file = open("org-chart-export.txt", "r")

# reading the file
data = my_file.read()

# replacing end splitting the text
# when newline ('\n') is seen.
data_into_list = data.split("\n")
print(data_into_list)
i=''
for j in data_into_list:
    # print(j)
    if 'LD ' in j:
        print(i,'-',j)
    i = j

# print(data_into_list)
my_file.close()
