/**
 * 方块类
 * 玩家跳跃的目标平台
 */

export class Block {
    constructor(x, y, width, height, type = 'normal') {
        this.x = x;
        this.y = y;
        this.width = width;
        this.height = height;
        this.type = type; // normal, wood, brick, ice, etc.
        this.passed = false; // 是否已经踩过
        this.sprite = null;
    }

    create() {
        this.sprite = new Laya.Sprite();
        
        // 根据类型绘制不同样式
        this.draw();
        
        this.sprite.x = this.x;
        this.sprite.y = this.y;
    }

    draw() {
        const g = this.sprite.graphics;
        
        // 方块主体
        let color = "#8B4513"; // 默认木质
        switch (this.type) {
            case 'normal':
                color = "#8B4513";
                break;
            case 'wood':
                color = "#A0522D";
                break;
            case 'brick':
                color = "#B22222";
                break;
            case 'ice':
                color = "#87CEEB";
                break;
            case 'grass':
                color = "#228B22";
                break;
        }
        
        // 绘制方块
        g.drawRect(0, 0, this.width, this.height, color);
        
        // 顶部高光
        g.drawRect(0, 0, this.width, 5, this.lightenColor(color, 30));
        
        // 侧面阴影
        g.drawRect(0, this.height - 5, this.width, 5, this.darkenColor(color, 30));
        
        // 添加纹理
        this.addTexture(g, color);
    }

    addTexture(g, color) {
        // 简单的纹理效果
        g.drawLine(5, 10, 5, this.height - 10, this.darkenColor(color, 20));
        g.drawLine(15, 10, 15, this.height - 10, this.darkenColor(color, 20));
        g.drawLine(25, 10, 25, this.height - 10, this.darkenColor(color, 20));
    }

    lightenColor(color, percent) {
        // 简化版本，实际应该解析 hex 颜色
        return color;
    }

    darkenColor(color, percent) {
        // 简化版本
        return "#654321";
    }

    getBounds() {
        return {
            x: this.x,
            y: this.y,
            width: this.width,
            height: this.height
        };
    }

    destroy() {
        if (this.sprite && this.sprite.parent) {
            this.sprite.parent.removeChild(this.sprite);
        }
    }
}
