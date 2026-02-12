import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    print("=" * 80)
    print("健康管理系统 - 数据处理工具")
    print("=" * 80)
    print()
    
    while True:
        print("请选择操作:")
        print("1. 数据预处理 (分析、标准化、异常检测、健康评分)")
        print("2. 数据清洗 (删除无效数据、修复缺失值、去重)")
        print("3. 数据验证 (完整性、一致性、合理性检查)")
        print("4. 查看数据概览")
        print("5. 修改数据")
        print("6. 生成扩展数据")
        print("0. 退出")
        print()
        
        choice = input("请输入选项 (0-6): ").strip()
        
        if choice == '0':
            print("退出程序")
            break
        elif choice == '1':
            print("\n正在运行数据预处理...")
            os.system("python data_preprocessing.py")
            input("\n按回车键继续...")
        elif choice == '2':
            print("\n正在运行数据清洗...")
            os.system("python data_cleaning.py")
            input("\n按回车键继续...")
        elif choice == '3':
            print("\n正在运行数据验证...")
            os.system("python data_validation.py")
            input("\n按回车键继续...")
        elif choice == '4':
            print("\n正在查看数据概览...")
            os.system("python show_data.py")
            input("\n按回车键继续...")
        elif choice == '5':
            print("\n正在打开数据修改工具...")
            os.system("python modify_data.py")
            input("\n按回车键继续...")
        elif choice == '6':
            print("\n正在生成扩展数据...")
            os.system("python generate_extended_data.py")
            input("\n按回车键继续...")
        else:
            print("无效选项，请重新输入")
        
        print()


if __name__ == '__main__':
    main()
