import matplotlib.pyplot as plt
import os

# 文件夹路径
folder_path = '/home/sbc/PycharmProjects/CFCQL/CFCQL-main/discrete/results/Q/bayes_iql__2s3z__bayes__2024-09-13_08-14-59'

# 循环处理 5 个 agent
for agent_id in range(5):
    # 构建文件路径
    file_path = os.path.join(folder_path, f'agent_{agent_id}_data.txt')

    # 读取txt文件中的数据
    y = []
    with open(file_path, 'r') as file:
        for line in file:
            y.append(float(line.strip()))  # 读取每一行的数据并去除换行符

    # 只处理第126个数据之后的部分
    # y = y[126:]

    # 计算平均值，每100步一个平均值
    averaged_y = [sum(y[i:i + 100]) / 100 for i in range(0, len(y), 100)]

    # 创建 x 轴，x 轴就是数据的行数
    x = list(range(1, len(averaged_y) + 1))

    # 绘制图表
    plt.plot(x, averaged_y, color=(69 / 255, 123 / 255, 157 / 255))
    plt.xlabel("100 step")
    plt.ylabel('q value')
    plt.title(f'Expert Model Agent {agent_id}')

    # 保存图表到同一文件夹下
    save_path = os.path.join(folder_path, f'agent_{agent_id}_q_values_plot.png')
    plt.savefig(save_path)
    plt.close()  # 关闭当前绘图，防止重叠

