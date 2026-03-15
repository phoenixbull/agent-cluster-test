/**
 * 输入处理类
 * 处理触摸、鼠标事件
 */

export class Input {
    constructor(player) {
        this.player = player;
        this.isTouching = false;
        this.touchStartX = 0;
        this.touchStartY = 0;
    }

    init() {
        const stage = Laya.stage;
        
        // 触摸事件
        stage.on(Laya.Event.MOUSE_DOWN, this, this.onMouseDown);
        stage.on(Laya.Event.MOUSE_UP, this, this.onMouseUp);
        
        // 触摸设备支持
        stage.on(Laya.Event.TOUCH_START, this, this.onTouchStart);
        stage.on(Laya.Event.TOUCH_END, this, this.onTouchEnd);
        
        console.log('👆 输入系统已初始化');
    }

    onMouseDown(e) {
        this.isTouching = true;
        this.touchStartX = e.stageX;
        this.touchStartY = e.stageY;
        this.player.startCharge();
    }

    onMouseUp(e) {
        if (!this.isTouching) return;
        this.isTouching = false;
        this.player.endCharge();
    }

    onTouchStart(e) {
        e.preventDefault();
        this.isTouching = true;
        this.touchStartX = e.stageX;
        this.touchStartY = e.stageY;
        this.player.startCharge();
    }

    onTouchEnd(e) {
        e.preventDefault();
        if (!this.isTouching) return;
        this.isTouching = false;
        this.player.endCharge();
    }

    destroy() {
        const stage = Laya.stage;
        stage.off(Laya.Event.MOUSE_DOWN, this, this.onMouseDown);
        stage.off(Laya.Event.MOUSE_UP, this, this.onMouseUp);
        stage.off(Laya.Event.TOUCH_START, this, this.onTouchStart);
        stage.off(Laya.Event.TOUCH_END, this, this.onTouchEnd);
    }
}
