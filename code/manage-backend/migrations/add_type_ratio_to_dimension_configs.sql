-- 训练维度配置增加「题型抽取比例」
-- NULL = 五种题型平均分配；示例：{"SINGLE_CHOICE":4,"MULTIPLE_CHOICE":2,"TRUE_FALSE":2,"FILL_BLANK":1,"APPLICATION":1}
ALTER TABLE training_dimension_configs
    ADD COLUMN IF NOT EXISTS type_ratio JSONB;
COMMENT ON COLUMN training_dimension_configs.type_ratio IS '题型抽取比例（按权重分配名额）；NULL 表示五种题型平均';
