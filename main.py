from data_system import Data_system
if __name__ == "__main__":
    data = Data_system()
    data.connect()
    # data.insert_data_apartments('shelf 4')
    # data.delete_data_apartments('Shelf 1')
    print(data.get_data_apartments())